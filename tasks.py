# SPDX-FileCopyrightText: 2021, 2023, 2024 LogicMonitor, Inc.
#
# SPDX-License-Identifier: LicenseRef-All-rights-reserved

"""``Invoke`` tasks."""

import dataclasses
import datetime
import enum
import os
import pathlib
import shlex
import shutil
import typing

import dotenv
import invoke
import pygit2  # type: ignore[import-untyped]
import semantic_version  # type: ignore[import-untyped]
import tomlkit
import urllib3

_PROJ_ROOT_PATH = pathlib.Path(__file__).parent.resolve()
_BUILD_DIR_PATH = _PROJ_ROOT_PATH / "build"
_PRIV_PYPI_REPO_ENV_PREFIX = "PRIVATE_PYPI_REPO_"
_PRIV_CONTAINER_IMG_REPO_ENV_PREFIX = "PRIVATE_CONTAINER_IMG_REPO_"


class _Executable(enum.StrEnum):
    """External executables called by script."""

    BUILDAH = "buildah"
    SKOPEO = "skopeo"


class _PyProjCfg:  # pylint: disable=too-few-public-methods
    """Python project config. from pyproject.toml."""

    def __init__(self, *, proj_root: pathlib.Path) -> None:
        """Load config. from pyproject.toml at proj. root.

        :param proj_root: proj. root dir.
        """
        self._cfg_path = proj_root / "pyproject.toml"
        self._cfg = typing.cast(
            dict[str, dict[str, typing.Any]],
            tomlkit.loads(self._cfg_path.read_text()))
        self.name: str = self._cfg["project"]["name"]
        self.version: str = self._cfg["project"]["version"]
        self.descr: str = self._cfg["project"]["description"]
        self.maintainer_name: str = (
            self._cfg["project"]["maintainers"][0]["name"])
        self.script_name: str = next(
            iter(self._cfg["project"]["scripts"].keys()))

    def bump_version(self, *, level: str) -> None:
        """Bump specified component of project version.

        :param level: level of version bump (major, minor, patch).
        """
        self._cfg["project"]["version"] = self.version = str(getattr(
            semantic_version.Version(self.version), f"next_{level}")())
        self._cfg_path.write_text(tomlkit.dumps(self._cfg))


@dataclasses.dataclass
class _ContainerImgRepoCfg:
    """Container image repo. config."""

    registry: str
    ns_: str
    username: str
    password: str

    @classmethod
    def from_env(cls, *, env_prefix: str) -> typing.Self:
        """Instantiate from env.

        :param env_prefix: prefix of repo. cfg. env. vars.
        :returns: class instance.
        """
        return cls(
            registry=os.environ[f"{env_prefix}REGISTRY"],
            ns_=os.environ.get(f"{env_prefix}NS", ""),
            username=os.environ[f"{env_prefix}USERNAME"],
            password=os.environ[f"{env_prefix}PASSWORD"])


class _GitRepo:
    """Git repo."""

    def __init__(self, *, proj_root: pathlib.Path) -> None:
        """Create repo. object from proj. root.

        :param proj_root: proj. root dir.
        """
        self._repo = pygit2.Repository(proj_root)

    @property
    def tagged_ver(self) -> str:
        """Get version from single existing HEAD version tag.

        :returns: version.
        :raises ValueError: if not exactly one version tag found.
        """
        ver_tags = [
            ref.shorthand for ref in self._repo.listall_reference_objects()
            if ref.name.startswith("refs/tags")
            and str(ref.peel().id) == str(self._repo.head.peel().id)
            and ref.shorthand.startswith("v")]
        try:
            ver: str = ver_tags.pop()[1:]
        except IndexError as exc:
            raise ValueError("No version tags present.") from exc
        if ver_tags:
            raise ValueError("More than one version tag present.")
        return ver

    def add_and_commit(self, *, msg: str) -> None:
        """Add all files to index and commit.

        :param msg: commit message.
        """
        config = self._repo.config
        # Assume highest precedence in each is last (bad libgit2 API).
        user_name = list(config.get_multivar("user.name")).pop()
        user_email = list(config.get_multivar("user.email")).pop()

        index = self._repo.index
        index.add_all()
        index.write()

        ref = self._repo.head.name
        # pylint: disable-next=no-member
        author = committer = pygit2.Signature(user_name, user_email)
        tree = index.write_tree()
        parents = [self._repo.head.target]
        self._repo.create_commit(ref, author, committer, msg, tree, parents)

    def tag_with_ver(self, *, version: str) -> None:
        """Tag HEAD with version.

        :param version: version string.
        :raises ValueError: if tag already exists.
        """
        commit = self._repo.head.peel()
        tags = [
            ref.shorthand for ref in self._repo.listall_reference_objects()
            if ref.name.startswith("refs/tags")
            and str(ref.peel().id) == str(commit.id)]
        if f"v{version}" in tags:
            raise ValueError("Tag already exists.")
        self._repo.create_tag(
            f"v{version}",
            str(commit.id),
            pygit2.enums.ObjectType.COMMIT,
            commit.author,
            f"Version {version}")


@dataclasses.dataclass
class _PyPIRepoCfg:
    """PyPI repo. config."""

    url: str
    url_pip_suffix: str
    username: str
    password: str

    @classmethod
    def from_env(cls, *, env_prefix: str) -> typing.Self:
        """Instantiate from env.

        :param env_prefix: prefix of repo. cfg. env. vars.
        :returns: class instance.
        """
        return cls(
            url=os.environ[f"{env_prefix}URL"],
            url_pip_suffix=os.environ.get(f"{env_prefix}URL_PIP_SUFFIX", ""),
            username=os.environ[f"{env_prefix}USERNAME"],
            password=os.environ[f"{env_prefix}PASSWORD"])

    @property
    def pip_env(self) -> dict[str, str]:
        """Generate pip env. vars from settings.

        :returns: env. vars consisting of PIP_INDEX_URL.
        """
        url = f"{self.url}{self.url_pip_suffix}"
        url_obj = urllib3.util.parse_url(url)
        url_obj_with_auth = urllib3.util.Url(
            url_obj.scheme,
            f"{self.username}:{self.password}",
            url_obj.host,
            url_obj.port,
            url_obj.path,
            url_obj.query,
            url_obj.fragment)
        return {"PIP_INDEX_URL": url_obj_with_auth.url}

    @property
    def twine_env(self) -> dict[str, str]:
        """Generate Twine env. vars from settings.

        :returns: Twine env. vars containing repo. URL, username and
            password.
        """
        return {
            "TWINE_REPOSITORY_URL": self.url,
            "TWINE_USERNAME": self.username,
            "TWINE_PASSWORD": self.password,
            }


class _PyPkg:
    """Python package."""

    def __init__(
        self,
        *,
        proj_root: pathlib.Path,
        build_dir_path: pathlib.Path,
        pypi_repo_cfg: _PyPIRepoCfg
    ):
        """Check for tagged version; store proj. root.

        :param proj_root: proj. root dir.
        :param build_dir_path: build dir.
        :param pypi_repo_cfg: PyPI repo. config.
        """
        self._proj_root = proj_root
        self._build_dir_path = build_dir_path
        self._pypi_repo_cfg = pypi_repo_cfg

    def clean(self) -> None:
        """Remove build artefacts."""
        try:
            shutil.rmtree(self._build_dir_path)
        except FileNotFoundError:
            pass

    def build(self, *, ctx: invoke.context.Context) -> None:
        """Build using `build` package.

        :param ctx: Invoke context.
        """
        cmd = [
            "python3",
            "-m",
            "build",
            "-o",
            str(self._build_dir_path),
            str(self._proj_root)]
        ctx.run(shlex.join(cmd))

    def publish(self, *, ctx: invoke.context.Context) -> None:
        """Publish to PyPI repo via Twine.

        :param ctx: Invoke context.
        """
        artefacts = [str(path) for path in self._build_dir_path.glob("*")]
        cmd = ["python3", "-m", "twine", "upload", *artefacts]
        ctx.run(shlex.join(cmd), env=self._pypi_repo_cfg.twine_env)


def _py_pkg_from_proj() -> _PyPkg:
    """Create Python package object from project.

    :returns: Python package object.
    """
    pypi_repo_cfg = _PyPIRepoCfg.from_env(
        env_prefix=_PRIV_PYPI_REPO_ENV_PREFIX)
    return _PyPkg(
        proj_root=_PROJ_ROOT_PATH,
        build_dir_path=_BUILD_DIR_PATH,
        pypi_repo_cfg=pypi_repo_cfg)


class _ContainerImg:
    """Container image."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *,
        proj_root: pathlib.Path,
        build_dir_path: pathlib.Path,
        py_proj_cfg: _PyProjCfg,
        pypi_repo_cfg: _PyPIRepoCfg,
        priv_container_img_repo_cfg: _ContainerImgRepoCfg,
        container_img_name: str
    ):
        """Store project params.

        :param proj_root: proj. root dir.
        :param build_dir_path: build dir. path.
        :param py_proj_cfg: Python project config.
        :param pypi_repo_cfg: PyPI repo. config.
        :param priv_container_img_repo_cfg: private container image
            repo. cfg.
        :param container_img_name: container image name.
        """
        self._proj_root = proj_root
        self._build_dir_path = build_dir_path
        self._pypi_repo_cfg = pypi_repo_cfg
        self._priv_container_img_repo_cfg = priv_container_img_repo_cfg
        self._py_proj_cfg = py_proj_cfg
        self._container_img_name = container_img_name
        self._tar_path = self._build_dir_path.joinpath(
            f"{self._container_img_name}-{self._py_proj_cfg.version}.tar")

    @property
    def _build_env(self) -> dict[str, str]:
        """Get env. for image build build-args.

        :returns: env.
        """
        return {
            "PRIVATE_CONTAINER_IMG_REPO_REGISTRY": (
                self._priv_container_img_repo_cfg.registry),
            "PRIVATE_CONTAINER_IMG_REPO_NS": (
                self._priv_container_img_repo_cfg.ns_),
            "PROJ_NAME": self._py_proj_cfg.name,
            "PROJ_DESCR": self._py_proj_cfg.descr,
            "PROJ_MAINTAINER_NAME": self._py_proj_cfg.maintainer_name,
            "PROJ_VER": self._py_proj_cfg.version,
            **self._pypi_repo_cfg.pip_env}

    def build(self, *, ctx: invoke.context.Context) -> None:
        """Build container image using Buildah.

        :param ctx: Invoke context.
        """
        self._build_dir_path.mkdir(parents=True, exist_ok=True)
        if self._priv_container_img_repo_cfg.ns_:
            registry = (
                f"{self._priv_container_img_repo_cfg.registry}"
                f"/{self._priv_container_img_repo_cfg.ns_}")
        else:
            registry = self._priv_container_img_repo_cfg.registry
        cmd = [
            _Executable.BUILDAH,
            "login",
            f"--username={self._priv_container_img_repo_cfg.username}",
            f"--password={self._priv_container_img_repo_cfg.password}",
            registry]
        ctx.run(shlex.join(cmd))
        cmd = [
            _Executable.BUILDAH,
            "bud",
            *[f"--build-arg={k}={v}" for k, v in self._build_env.items()],
            "-t",
            self._container_img_name,
            str(self._proj_root)]
        ctx.run(shlex.join(cmd))
        cmd = [
            _Executable.BUILDAH,
            "push",
            self._container_img_name,
            f"oci-archive:{self._tar_path}:{self._container_img_name}"]
        ctx.run(shlex.join(cmd))

    def publish(self, *, ctx: invoke.context.Context) -> None:
        """Publish container image to registry.

        :param ctx: Invoke context.
        """
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        img_tag = f"{self._py_proj_cfg.version}_{timestamp_str}"
        if self._priv_container_img_repo_cfg.ns_:
            url = (
                f"docker://{self._priv_container_img_repo_cfg.registry}"
                f"/{self._priv_container_img_repo_cfg.ns_}"
                f"/{self._container_img_name}:{img_tag}")
        else:
            url = (
                f"docker://{self._priv_container_img_repo_cfg.registry}"
                f"/{self._container_img_name}:{img_tag}")
        cmd = [
            _Executable.SKOPEO,
            "copy",
            f"--dest-username={self._priv_container_img_repo_cfg.username}",
            f"--dest-password={self._priv_container_img_repo_cfg.password}",
            f"oci-archive:{self._tar_path}",
            url]
        ctx.run(shlex.join(cmd))


def _container_img_from_proj() -> _ContainerImg:
    """Create container image object from project.

    :returns: container image object.
    """
    py_proj_cfg = _PyProjCfg(proj_root=_PROJ_ROOT_PATH)
    pypi_repo_cfg = _PyPIRepoCfg.from_env(
        env_prefix=_PRIV_PYPI_REPO_ENV_PREFIX)
    priv_container_img_repo_cfg = _ContainerImgRepoCfg.from_env(
        env_prefix=_PRIV_CONTAINER_IMG_REPO_ENV_PREFIX)
    return _ContainerImg(
        proj_root=_PROJ_ROOT_PATH,
        build_dir_path=_BUILD_DIR_PATH,
        py_proj_cfg=py_proj_cfg,
        pypi_repo_cfg=pypi_repo_cfg,
        priv_container_img_repo_cfg=priv_container_img_repo_cfg,
        container_img_name=py_proj_cfg.name.replace(".", "-").replace(
            "_", "-"))


def _bump_version(*, level: str) -> None:
    """Bump specified component of version, commit and tag.

    :param level: level of version bump (major, minor, patch).
    """
    py_proj_cfg = _PyProjCfg(proj_root=_PROJ_ROOT_PATH)
    py_proj_cfg.bump_version(level=level)
    commit_msg = f"{level.capitalize()}-bump version to {py_proj_cfg.version}"
    git_repo = _GitRepo(proj_root=_PROJ_ROOT_PATH)
    git_repo.add_and_commit(msg=commit_msg)
    git_repo.tag_with_ver(version=py_proj_cfg.version)


def _check_versions_match() -> bool:
    """Check Git version tag exists and matches version from proj. cfg.

    :returns: whether values match.
    """
    try:
        tagged_ver = _GitRepo(proj_root=_PROJ_ROOT_PATH).tagged_ver
    except ValueError:
        return False
    return tagged_ver == _PyProjCfg(proj_root=_PROJ_ROOT_PATH).version


@invoke.task  # type: ignore[attr-defined]
def tests_run(ctx: invoke.context.Context) -> None:
    """Run tests.

    :param ctx: Invoke context.
    """
    pypi_repo_cfg = _PyPIRepoCfg.from_env(
        env_prefix=_PRIV_PYPI_REPO_ENV_PREFIX)
    cmd = ["python3", "-m", "nox", "--force-color"]
    ctx.run(shlex.join(cmd), env=pypi_repo_cfg.pip_env)


@invoke.task  # type: ignore[attr-defined]
def version_bump_major(_ctx: invoke.context.Context) -> None:
    """Bump major component of version, commit and tag.

    :raises SystemExit: if Git version tagging failed.
    """
    try:
        _bump_version(level="major")
    except ValueError as exc:
        raise SystemExit from exc


@invoke.task  # type: ignore[attr-defined]
def version_bump_minor(_ctx: invoke.context.Context) -> None:
    """Bump minor component of version, commit and tag.

    :raises SystemExit: if Git version tagging failed.
    """
    try:
        _bump_version(level="minor")
    except ValueError as exc:
        raise SystemExit from exc


@invoke.task  # type: ignore[attr-defined]
def version_bump_patch(_ctx: invoke.context.Context) -> None:
    """Bump patch component of version, commit and tag.

    :raises SystemExit: if Git version tagging failed.
    """
    try:
        _bump_version(level="patch")
    except ValueError as exc:
        raise SystemExit from exc


@invoke.task  # type: ignore[attr-defined]
def python_package_clean(_ctx: invoke.context.Context) -> None:
    """Remove Python package build artefacts."""
    _py_pkg_from_proj().clean()


@invoke.task  # type: ignore[attr-defined]
def python_package_build(ctx: invoke.context.Context) -> None:
    """Build Python package.

    :param ctx: Invoke context.
    :raises SystemExit: if proj./Git tag versions don't match.
    """
    if not _check_versions_match():
        raise SystemExit("Proj./Git tag version mismatch, aborting.")
    _py_pkg_from_proj().build(ctx=ctx)


@invoke.task  # type: ignore[attr-defined]
def python_package_publish(ctx: invoke.context.Context) -> None:
    """Publish Python package to PyPI repo.

    :param ctx: Invoke context.
    :raises SystemExit: if proj./Git tag versions don't match.
    """
    if not _check_versions_match():
        raise SystemExit("Proj./Git tag version mismatch, aborting.")
    _py_pkg_from_proj().publish(ctx=ctx)


@invoke.task  # type: ignore[attr-defined]
def container_image_build(ctx: invoke.context.Context) -> None:
    """Build container image.

    :param ctx: Invoke context.
    :raises SystemExit: if proj./Git tag versions don't match.
    """
    if not _check_versions_match():
        raise SystemExit("Proj./Git tag version mismatch, aborting.")
    _container_img_from_proj().build(ctx=ctx)


@invoke.task  # type: ignore[attr-defined]
def container_image_publish(ctx: invoke.context.Context) -> None:
    """Publish container image to registry.

    :param ctx: Invoke context.
    :raises SystemExit: if proj./Git tag versions don't match.
    """
    if not _check_versions_match():
        raise SystemExit("Proj./Git tag version mismatch, aborting.")
    _container_img_from_proj().publish(ctx=ctx)


dotenv.load_dotenv()

namespace = invoke.Collection()  # type: ignore[attr-defined]

tests_ns = invoke.Collection("tests")  # type: ignore[attr-defined]
namespace.add_collection(tests_ns)
tests_ns.add_task(tests_run, "run")  # type: ignore[arg-type]

version_ns = invoke.Collection("version")  # type: ignore[attr-defined]
namespace.add_collection(version_ns)
version_ns.add_task(version_bump_major, "bump-major")  # type: ignore[arg-type]
version_ns.add_task(version_bump_minor, "bump-minor")  # type: ignore[arg-type]
version_ns.add_task(version_bump_patch, "bump-patch")  # type: ignore[arg-type]

python_package_ns = invoke.Collection(  # type: ignore[attr-defined]
    "python-package")
namespace.add_collection(python_package_ns)
python_package_ns.add_task(
    python_package_clean, "clean")  # type: ignore[arg-type]
python_package_ns.add_task(
    python_package_build, "build")  # type: ignore[arg-type]
python_package_ns.add_task(
    python_package_publish, "publish")  # type: ignore[arg-type]

container_image_ns = invoke.Collection(  # type: ignore[attr-defined]
    "container-image")
namespace.add_collection(container_image_ns)
container_image_ns.add_task(
    container_image_build, "build")  # type: ignore[arg-type]
container_image_ns.add_task(
    container_image_publish, "publish")  # type: ignore[arg-type]
