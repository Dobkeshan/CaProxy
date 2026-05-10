import os
import tempfile

class AppConfig:
    local_host = "127.0.0.1"
    local_proxy_port = 8080
    tor_socks_port = 9150
    tor_control_port = 9151
    runtime_dir = os.path.join(tempfile.gettempdir(), "tor_proxy_runtime")
    torrc_path = os.path.join(runtime_dir, "torrc")
    data_dir = os.path.join(runtime_dir, "data")
    binary_dir = os.path.join(runtime_dir, "bin")
    tor_bin = os.path.join(binary_dir, "tor")
    pt_bin = os.path.join(binary_dir, "obfs4proxy")
    built_in_bridges = [
        "obfs4 57.128.57.245:3099 D655AC9C21147BB62C781149150F0E723C4F8FBC cert=fnU2eGPmE6L53eXZf/29d1JloUD2XI/4KHNImTquPr/eBvkrOuuutIlpwvJsZTV1NvZ4aw iat-mode=0",
        "obfs4 91.134.99.182:26566 B5D7274F4267D73372BBF8C6446C3AF2D4399A4B cert=eXB5PBSwA+Y6Selwz245/3gZWsskMoJDZcBBccAxrqTtT7OLAwSguf9z2tHU5mV3YkgjIw iat-mode=0"
    ]