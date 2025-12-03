# Contexts

Contexts in ngcsimlib are the top level container that holds everything used to
define the model. On their own they have no runtime logic, they rely on their
internal processes and component to build a working model.

## Defining a Context

To define a context ngcsimlib leverages the `with` block meaning that to create
a new context simply start with `with Context("myContext") as ctx:` and a new
context will be created. (Important note: names are unique, if a context is
created with the same name they will be the same context and thus there might be
conflicts). This defined context does not do anything on its own.

## Adding Components

To add components to the context simply initialize components while inside
the `with` block of the context. Any component defined while inside the block
will automatically be added and tacked by the context object.

## Wiring Components

Inside a model components will need to pass data to one another that setup is
done here inside the context. To connect the compartments of two components
follow the pattern `mySource.output >> myDestination.input` where output and
input are compartments inside their respective components. This will ensure that
when processes are being run the value will flow properly from component to
component.

### Operators

There is a special type of wire called an operator that performs a simple
operation on the compartment values as the data flows from one component to
another. Generally these are use for simple math operations such as
negation `Negate(mySource.output) >> myDestination.input` or the summation of
multiple compartments into
one `Summation(mySource1.output, mySource2.output, ...) >> myDestination.input`.
These can be chained, so it would be possible to negate one or more of the inputs
to the summation.

## Adding Processes

To add processes to the context simple initialize the process and add all of its
steps while inside the `with` block of the process.

## Exiting the `with` block

When the context exits the `with` block it will recompile the entire model. This
means that all parts of the model that needed to be compiled before views (such
as the compiled methods of a process) needs to happen after the `with` block is
exited. Behind the scenes this is calling `recompile` on the context, it is
possible to manually trigger the recompile step but that can break certain
connections so use this functionality sparingly.

## Saving and Loading

The context's one unique job is the handling of the saving and loading of models
to disk. By default, calling `save_to_json(...)` will create the correct file
structure and files needed and load the context in the future. To load a model
calling `Context.load(...)` will load the context in from a directory, something
important to note while loading in a context is that it is effectively
recreating the components with their initial values using their arguments and
keywords arguments (excluding those that can't be serialized). This means that
if you have a trained model ensure that your components have a save method
defined that will handle the saving and loading of all values in their
compartments.  