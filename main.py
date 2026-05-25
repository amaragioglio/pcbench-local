import multiprocessing as mp

from pcbench.cli import main


if __name__ == "__main__":
    mp.freeze_support()
    main()
