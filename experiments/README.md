- The environment to execute the simulations on G5k is ready. We need:
  1. Access G5k and reserve a node.
  2. Nix installed,
  3. Nix environment (with Batsim, Batsched, ...) deployed,
  4. This repository cloned inside g5k.

- Step by step:
  1) To access and reserve a node on G5k:
     # To access G5k
     ssh login@access.grid5000.fr
     ssh site (aka. ssh Grenoble)

     # Ask for a reservation (3 hours)
     oarsub -l walltime=03:00 -I

     Once the reservation is ready, you will have access to another shell (nix-shell)

  2) To install Nix:

     sudo-g5k curl -L https://nixos.org/nix/install | sh

     # To activate Nix
     source /home/adasilva/.nix-profile/etc/profile.d/nix.sh

  3) To create and deploy the nix-environment

    a) To deploy the nix-env with Batsim, Batsched and etc:

      nix-shell --pure ./nix-env/nix-env.nix

      Once the environment is ready, you will be able to use batsim, batsched and etc.

  4) To clone this repository and run the simulations

    a) To acces the experiments folder
      cd job_partitioning/experiments

    b) Use robin to execute the simulation expe_test_mustang.yaml
      First, be sure that the folde test_mustang already exists in the results folder

      mkdir results
      mkdir results/test_mustang

      robin ./expe_partitioned_mustang.yaml

      Once ready, the results will be in results/test_mustang
