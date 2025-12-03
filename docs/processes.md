# Processes

Processes in ngcsimlib are a way of defining a specific transition across a
given model. They take in as many compilable method's across any number of
components and produce a single top level method and a varying number of
submethods needed to execute the entire chain of compilable methods in one step.
This is done to interface nicely with just in time compilers and minimize the
amount of read and write calls done across the chain of methods.

## Building the chain

Building the chain that a process will use is done in an iterative process. Once
the process object is created steps are added using either `.then()` or `>>`.
As an example

```
myProcess.then(myCompA.forward).then(myCompB.forward).then(myCompA.evolve).then(myCompB.evolve)
```

or

```
myProcess >> myCompA.forward >> myCompB.forward >> myCompA.evolve >> myCompB.evolve
```

In both cases this process will chain the four methods together into a single
step, only updating the final state all steps are complete.

## Types of processes

There are two types of processes, the above example would be with what is
referred to as a `MethodProcess`, these are used to chain together any
compilable
methods from any number of different components. The second type of process,
called a `JointProcess`, is used to chain together entire processes.
JointProcesses are especially useful if there are multiple method processes that
need to be called but different orders of the processes are needed at different
times.

## Extras

There are a few extra methods that come standard with each process type that can
be useful for both regular operation and debugging.

### Viewing the compiled method

Behind the scenes a process is transforming and compiling down all the steps
used to build it, these means that the exact code it is running to do its
calculation is not what the user wrote. To allow for the end user to view and
make sure that the two pieces of code; theirs and the compiled version, are
equivalent every process has a `view_compiled_method()` call that can be used
after the model is compiled. This call will return the code that it is running
as a string. There will be some stark differences between the produced code and
the code in the components used to build the steps. Please refer to the
compiling page for a more indepth guide to comparing the outputs.

### Needed Keywords

As some methods will require external values such as `t` or `dt` for a given
execution a process will also track all the keyword arguments that are needed to
run their compiled process. To view which keywords a given process is expected
calling `get_keywords()`. This is mostly used for debugging or a sanity check.

### Packing keywords

To add onto the needed keywords the process also provides an interface to
produce the keywords needed to run in the form of two methods. The first method
is `pack_keywords(...)`, this method packs together a single row of values
needed to run a single execution of the process. The arguments are
the `row_seed` which is a seed to be passed to all the keyword generators (only
needed if generators are being used). The second set of arguments are keyword
arguments that are either constant `dt=0.1` or
generators `lambda row_seed: 0.1 * row_seed`. The second method for generating
the keywords for a process is with `pack_rows(...)`. This method created many
sets of keywords needed to run multiple iterations of the process. The arguments
are slightly different, first it now has a `length` argument to indicate the
number of rows being produced, second it has a `seed_generator` use to generate
the seed of each row (for example to have only even
seeds `seed_generator = lambda x: 2 * x`) if the generator
is `None` `seed_generator = lamda x: x` is used. After that the same keyword
arguments to define the needed parameters is used as in `pack_keywords`    

