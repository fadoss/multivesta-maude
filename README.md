### Statistical analysis of probabilistic Maude specifications with MultiVeStA

The `mvmaude` tool integrates the probabilistic Maude strategy language into the [MultiVeSta](https://github.com/andrea-vandin/MultiVeStA) tool for the analysis of statistical models. Other simpler ways of assigning probabilities to Maude specifications are available too. The requirements for running this program are:

* [Java](https://openjdk.java.net) and the [MultiVeSta](https://github.com/andrea-vandin/MultiVeStA/wiki) tool (the `multivesta.jar` file), which can be downloaded from its [website](https://github.com/andrea-vandin/MultiVeStA/wiki/Integration-with-Python-model-simulator).
* [Python](https://www.python.org) 3.7 or greater and the [`maude`](https://pypi.org/project/maude) Python library. It can be installed with `pip install maude`.
* For any assignment method except `step` (see below), the [`umaudemc`](https://github.com/fadoss/umaudemc) tool is required. It can be installed with `pip install umaudemc`.

It is used as follows:

```bash
$ ./mvmaude <Maude file> <initial term> [<strategy>] <MultiQuaTEx query file> [--method <method>]
```

The `--help` flag can be passed to show more command line options. Arguments after `--` are directly passed to MultiVeSta (the list of options of this tool can be obtained with `java -jar multivesta.jar -c -help`). Adding the directory containing `mvmaude` to the system path would allow invoking this command from other locations.

The `method` option determines how probabilities are assigned to the Maude model. All [options](https://github.com/fadoss/umaudemc/#specification-of-probabilities) available in the `pcheck` command of `umaudemc` are available here, except those prefixed by `mdp-` since Markov decision processes are not appropriate for statistical analysis.
In addition, there are the following options: 

* `step` uses the given probabilistic strategy as the step of the simulation, which is repeated forever.
* `strategy` controls the system using the given probabilistic strategy, but the steps of the simulation are the rewrites that occur during the execution. For a better performance, backtracking and exhaustive exploration are disabled, so the execution is only faithful to the semantics when the strategy is failure-free.
* `strategy-full` does the same as `strategy` but respecting the semantics of the strategy. The full reachable graph will be expanded before taking the first step.

In principle, the given strategy must be free of unquantified nondeterminism. The `strategy` method resolves nondeterministic choices uniformly at random, and the other methods may choose one option arbitrarily (issuing a warning or even failing in `strategy-full`).

MultiQuaTEx queries may evaluate Maude terms with the `s.rval` function. These terms should be written as strings, reduce to a Boolean, integer, or floating-point values, and they may contain at most one distinct variable, which will be substituted by the current state of the simulation. The strings `time`, `steps`, and `completed` are directly interpreted by MultiVeSta as the current simulation time, the number of steps, and whether the simulation is complete.

More information can be found in the model checkers' [manual](https://maude.ucm.es/strategies/modelchecker-manual.pdf). This manual also describes the `scheck` command of the [`umaudemc`](https://github.com/fadoss/umaudemc) tool as an alternative to estimate QuaTEx queries under the same probability assignment methods.
