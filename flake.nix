{
  description = "Simple Tito nix flake";

  inputs = {
    nixpkgs.url      = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    flake-utils.url  = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, rust-overlay, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
          config.allowUnfree = true;
        };
      in
      {
        devShells.default = with pkgs; mkShell {
          buildInputs = [
            rust-bin.stable.latest.complete
          ];
          packages = with pkgs; [
            gdb
            bacon
            python313Packages.pygments # for personal gdb-dashboard use
            cargo-expand
            pkg-config
            openssl
          ];
          shellHook = ''
            export SHELL=${pkgs.lib.getExe pkgs.bashInteractive}
          '';
        };
        devShells.nightly = with pkgs; mkShell {
          buildInputs = [
            (rust-bin.selectLatestNightlyWith (toolchain: toolchain.complete))
          ];
          packages = with pkgs; [
            gdb
            gdbgui
            bacon
            python313
            python313Packages.pygments # for personal gdb-dashboard use
            python313Packages.requests
            python313Packages.ruff
            cargo-expand
          ];
          shellHook = ''
            export SHELL=${pkgs.lib.getExe pkgs.bashInteractive}
          '';
        };
      }
    );
}
