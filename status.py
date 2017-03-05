class Status(dict):
    ok = None

    def __init__(self, result, msg=""):
        dict.__init__(self, ok=self.ok, msg=msg, result=result)
        self.msg = msg
        self.result = result


class StatusOk(Status):
    ok = True


class StatusError(Status):
    ok = False


class StatusParam(dict):
    def __init__(self, param_name, param_value):
        dict.__init__(self, param_name=param_name, param_value=param_value)
