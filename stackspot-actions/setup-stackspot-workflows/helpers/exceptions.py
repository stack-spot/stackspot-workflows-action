class ActionException(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class CloningRepoException(ActionException):
    def __init__(self):
        super().__init__(msg="Git clone failure")


class ApplyPluginSetupRepositoryException(ActionException):
    def __init__(self):
        super().__init__(msg="")


class RepositoryNeedsToExists(ActionException):
    def __init__(self):
        super().__init__(msg="Repository needs to exist! Quiting...")


class ProjectNeedsToExists(ActionException):
    def __init__(self):
        super().__init__(msg="Project needs to exist! Quiting...")
