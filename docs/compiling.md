# Compiling
The term compiling for ngcsimlib refers to automatic step that happens inside a context that produces a transformed method for all of its components. This step is the most complecated part of the library and generally does not need to be touched or interacted with. Nevertheless this section will cover all the steps that it does at a high level. There is an expectation that the reader has an understanding of python abstract syntax trees, globals, and how to dynamically compile python code to run.

## The decorator
In ngcsimlib there is a decorator marked as `@compilable` that is used to add a flag to methods that the user wants to compile. On its own it doesn't do anything but this lets the parser distinguish between method that should be compiled and methods that should be ignored.

## Step by Step
The process started by telling the parser to compile a specific object.

### Step 1: Compile Children
The first step to compile any object is to make sure that all the compilable objects of the top level object are compiled. So it loops through all the whole object and compiles each part that it finds that is flagged as compilable and is an instance of a class.

### Step 2: Extract Methods to Compile
While the parser is looping through all the parts of the top level object it is also extracting the methods on the object that are flagged as compilable with the decorator. It stores them for later but this lets the parser only loop over the object once.

### Step 3: Parse Each Method
As each method is its own entry point into the compiler the step will run for each method in the top level object

### Step 3a: Set up Transformer
The step sets up a ContextTransformer which is a ask.NodeTransformer and will convert the method from a class method with the use of `self` and other methods that need to be removed into their more context friendly counterpart.

### Step 3b: Transform the function
There are quite a few pieces of common python that need to be transformed. This step happens with the overall goal of replacing all object focused parts with a more global view. This means compartment's `.get` and `.set` calls are replaced with direct setting and getting from the global state based on the compartment's target. It also means that all temporally constant values such as `batch_size` are moved into the globals space for that specific file and replaced with the naming convention of `object_path_constant`. One more step that this does is ensure that there is no branching in the code. Specifically if there is a brach such as an if statement it will evaluate it and only keep the branch it will traverse down. This means that there can not be any branch logic based on inputs or computed values (this is a common restriction for just in time compiling). 

### Step 3c: Parse Sub-Methods
As it is possible to have other class methods that are not marked as entry points for compilation but need to be compiled as step 3b happens it tracks all the sub-methods needed, this step goes through and repeats steps 3a and 3b for each of them with a naming convention similar to the temporally constant values for each method.

### Step 3d: Compile the AST
Once we have all the needed namespace and globals needed to execute the method properly transformed the method is compiled with python and executed.

### Step 3e: Binding
The final step per method is to bind it to the original method, this replaces the method with an object which when called with act like the normal uncompiled version but has the addition of the `.compiled` attribute which contains all the compiled information to be used later. This allows for the end user to call `myComponent.myMethod.compiled()` and have it run. The exact type for `compiled` value can be found in `ngcsimlib._src.parser.utils:CompiledMethod`.

### Step 4: Finishing Up
Some objects such as the processes have more steps to modify themselves or their compiled methods to align themselves with needed functionality but that is found in each class's expanded `compile` method and should be referred to by looking at those methods specifically.    