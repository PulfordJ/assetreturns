{
  description = "Asset returns calculator with Jupyter notebook";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, pyproject-nix, uv2nix, pyproject-build-systems }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        # Load the workspace from uv.lock (only if it exists)
        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

        # Create overlay with build systems
        overlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };

        # Create the Python package set
        python = pkgs.python311;
        pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope(
          pkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
          ]
        );

        # Build the virtual environment
        venv = pythonSet.mkVirtualEnv "assetreturns-env" workspace.deps.all;

        # Bootstrap shell (for generating uv.lock before venv exists)
        bootstrapShell = pkgs.mkShell {
          packages = [
            pkgs.uv
            python
          ];
        };

      in
      {
        # App for running Jupyter notebook
        apps.default = {
          type = "app";
          program = "${venv}/bin/jupyter-notebook";
        };

        apps.notebook = {
          type = "app";
          program = "${venv}/bin/jupyter-notebook";
        };

        apps.lab = {
          type = "app";
          program = "${venv}/bin/jupyter-lab";
        };

        # Development shell with full environment
        devShells.default = pkgs.mkShell {
          packages = [
            venv
            pkgs.uv
          ];

          shellHook = ''
            # Ensure we use the virtual environment's Python
            export VIRTUAL_ENV="${venv}"
            export PATH="${venv}/bin:$PATH"

            echo "🐍 Python development environment loaded"
            echo "   Python: $(python --version)"
            echo "   Jupyter: $(jupyter --version | head -n1)"
            echo ""
            echo "Available commands:"
            echo "   jupyter notebook  - Start Jupyter notebook"
            echo "   jupyter lab       - Start Jupyter Lab"
            echo "   uv                - UV package manager"
            echo ""
            echo "Quick start:"
            echo "   nix run            - Launch Jupyter notebook"
            echo "   nix run .#lab      - Launch Jupyter Lab"
          '';
        };

        # Bootstrap shell (for initial setup without uv.lock)
        devShells.bootstrap = bootstrapShell;

        # Package the environment
        packages.default = venv;
      }
    );
}
