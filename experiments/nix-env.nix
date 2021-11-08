{ nur-kapack ? import
    ( fetchTarball "https://github.com/oar-team/nur-kapack/archive/master.tar.gz")
  {}
}:

with nur-kapack.pkgs;

let
  self = rec {
    experiment_env = mkShell rec {
      name = "experiment_env";
      buildInputs = [
        # simulator
        nur-kapack.batsim
        # scheduler implementations
        nur-kapack.batsched
        nur-kapack.pybatsim
        # misc. tools to execute instances
        nur-kapack.batexpe
      ];
    };
  };
in
  self.experiment_env