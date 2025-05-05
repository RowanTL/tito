{
  description = "A flake for developing in python with a few libraries with vscode";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11";
  };

  outputs = { nixpkgs, ... }:
  let system = "x86_64-linux"; pkgs = import nixpkgs { system = "${system}"; config.allowUnfree = true; }; in
  {
    devShells."${system}".default =
      pkgs.mkShellNoCC {
        buildInputs = [ pkgs.bashInteractive ];
        packages = with pkgs; [
          (python3.withPackages (pypkgs: with pypkgs; [
            pandas
            polars
            matplotlib
            numpy
            jupyter
            pip
            notebook
            xlrd
            statsmodels
            jupyterlab
            ipykernel
            pyzmq
            scikit-learn
            jupytext
            seaborn
            spyder
            fastexcel
          ]))
          octaveFull
          zeromq
          (vscode-with-extensions.override {
            vscodeExtensions = with vscode-extensions; [
              ms-python.python
              ms-azuretools.vscode-docker
              ms-toolsai.datawrangler
              ms-toolsai.jupyter
              bbenoist.nix
              mechatroner.rainbow-csv
              donjayamanne.githistory
              ms-python.vscode-pylance
              ms-python.debugpy
              thenuprojectcontributors.vscode-nushell-lang
            ];
          })
        ];
        shellHook = ''
          export SHELL=${pkgs.lib.getExe pkgs.bashInteractive}
        '';
      };
  };
}

