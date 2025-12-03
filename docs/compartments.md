# Compartments

Inside ngcsimlib there is the global state as the backbone of any given model.
This global state is the culmination of all the dynamic or changing parts of the
model. Each value that builds this state is stored in a special container that
helps track these changes known as a Compartment.

## Practical Information

Practically when working with compartments there are a few simple things to keep
in mind and the rest is all behind the scenes bookkeeping. The first piece to
keep in mind is that each compartment holds a value and thus setting a
compartment with `myCompartment = newValue` will not function as intended as
this will overwrite the python object that is the compartment with `newValue`.
Instead, make use of the `.set()` method to update the value stored inside a
compartment so `myCompartment = newValue` becomes `myCompartment.set(newValue)`.
The second piece of information is that to retrieve a value from the compartment
use `myCompartment.get()`. These methods to get and set data inside a
compartment are the two main pieces to remember.

## Technical information

The follow sections are devoted to more technical information regarding how a
compartment functions in the broader scope of ngcsimlib and how to leverage that
information.

### How data is stored

The data stored inside a compartment is not actually stored inside a
compartment. Instead, it is stored inside the global state and each compartment
just holds the path or `key`, in the global state to pull a specific piece of
information. As such it is technically possible to manipulate the value of a
compartment without actually touching the compartment object created in a
component. By default, compartments have safeguards to prevent this from happening
accidentally but directly addressing the compartment in the global state has no
such safeguards.

### What is targeting

As discussed in the model building section there is a concept of wiring together
different compartments of different components. These wires are created through
the concept of targeting. In esscence targeting is just updating the path stored
in a compartment with the path of a different compartment. This means that if
the targeted compartment goes to retireve the value stored in it, it will
actually retrieve the value for the a different compartment. When a compartment
is in this state where it is targeted at another compartment it is set to read
only meaning that it can not modify a different compartment.


