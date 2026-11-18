{
  # lib,
  buildPythonPackage,
  fetchPypi,
  # setuptools,
  # wheel,
  # asyncio-socks-server,
  pkgs,
}:

# pkgs.buildFHSEnv {
buildPythonPackage {
  pname = "reticulum-ip";
  version = "0.1";
  format = "pyproject";
  __structuredAttrs = true;

  src = ./.;

  dependencies = with pkgs; [
    python314Packages.rns
    # python314Packages.asyncio-socks-server
  ];

  nativeBuildInputs = with pkgs; [ autoPatchelfHook ];

  build-system = [ pkgs.python314Packages.setuptools ];

  # has no tests
  doCheck = false;

  meta = {
    # [...]
  };
}
# }
