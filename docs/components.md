# Components

Living one step above compartments in a model hierachy rests the component. The
components hold a collection of both temporally constant values and dynamic
compartments, in addition they are the lowest place where logic governing the
dynamics of a system are defined. Generally components are going to be the
building blocks that are reused multiple times throughout a model to create a
final dynmical system.

## Temporally Constant vs Dynamic Compartments

One important distinction that needs to be highlighted inside a component is the
difference between a temporally constant value and a dynamic compartment.
Starting with compartments these values that change over time, generally they
will have the type `ngcsimlib.Compartment` and be used to track internal values
of the component. These values can be ones such inputs, decaying values,
counters, etc. The second catagory of values are temporally constant, these are
values that will remain fixed on the model is constructed. These values tend to
include ones such as matrix shapes and coefficients.

## Defining Compilable Methods

Inside a component it is expected that there are methods used to govern the
temporal dynamics of a system. These compilable methods are decorated
with `@compilable` and are defined like any regular method. Inside a compilable
method there will be access to `self`, meaning that to reference a compartment's
value it is `self.myCompartment.get()`. The only requirement is that any method
decorated can not have a return value, values should be stored inside their
respective compartments. In an external step from defining the component a
transformer will change all of these methods into ones that function with the
rest of ngcsimlib.