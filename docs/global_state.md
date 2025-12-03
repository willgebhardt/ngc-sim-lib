# The Global State

As ngcsimlib is a simulation library focused on temporal models; or models that
change over time there, all models have some concept of a state. These states
might be comprised of a single value that changes or of a complex set of values
that when combined all together make up the dynamical system for the model. In
both cases these sets of values are stored in what is known as the global state.

## Interacting with the global state

Since the global state will contain a large amount of information about a given
model there is a need to be able to interact with and modify the values in the
global state. In most use cases this is not done directly. The most common way
to interact with the global state is through the use of the state manager. The
state manager exists to provide a set of helper methods for interacting with the
global state. While the manager is there to assist you it is not going to stop
you from changing the state, or breaking the state. When changing the state
beyond setting it as a result of processes be careful not to add or remove
anything that is needed for your model.

### Adding new fields to the global state

If you are new to using ngcsimlib and looking for a way to add values to the
global state, stop for a moment. Unless you know exactly what you are doing do
not manually add values to the global state, instead see compartments, or
components as those are the most common ways for adding fields to the global
state.

If you are actually trying to manually add values to the global state it is done
through the use of the `add_key` method. This will create the appropriate key in
the global state for at the given path and name, and it will be retrieved
with `from_key` calls. This value however is not linked to a compartment and
thus will be hard to get working properly in the compiled methods without some
specific references.

### Getting the current state

To get the current state simply call `global_state_manager.state` this will give
you a copy of the current state, meaning that any modifications made to it are
not reflected in the global state.

### Updating the global state

To manually update the global state after modifying a local
copy `global_state_manager.state = new_state` can be uased. This will update the
state with the `.update` call for dictionaries meaning that a partial state will
still update correctly.

