
class RepoAlreadyExistsError(Exception):
    pass


class RepoDoesNotExistError(Exception):
    pass


class CloningRepoError(Exception):
    pass


class UnauthorizedError(Exception):
    pass


class NotFoundError(Exception):
    pass


class GitUserSetupError(Exception):
    pass


class WorkspaceShouldNotInUseError(Exception):
    pass


class ApplyPluginSetupRepositoryError(Exception):
    pass
