from botpy.connection import ConnectionState

_raw_payloads = {}
def get_raw_payload(msg_id: str) -> dict:
    return _raw_payloads.pop(msg_id, {})

def patch():
    def parse_group_message_create(self, payload):
        _message = GroupMessage(self.api, payload.get("id", None), payload.get("d", {}))
        msg_id = payload.get("id", "")
        if msg_id:
            _raw_payloads[msg_id] = payload.get("d", {})
        self._dispatch("group_message_create", _message)
    ConnectionState.parse_group_message_create = parse_group_message_create