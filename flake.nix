{
  description = "A flake for developing in python with a few libraries with vscode";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11";
    unixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { nixpkgs, unixpkgs, ... }:
  let
    system = "x86_64-linux";

    # overlay = final: prev: {
    #   python312 = prev.python312.override {
    #     packageOverrides = pyFinal: pyPrev: {
    #       fastexcel = unixpkgs.legacyPackages.${system}.python312Packages.fastexcel;
    #     };
    #   };
    # };

    pkgs = import unixpkgs {
      system = "${system}";
      config.allowUnfree = true;
      # overlays = [ overlay ];
    };
  in
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
            yfinance
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
          export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
            pkgs.stdenv.cc.cc.lib
          ]}:$LD_LIBRARY_PATH
        '';
      };
  };
}

