# api-demo.py - tangled from GENTLE_SLOPE.org to demonstrate 
# an idea, how the interactive recording can be turned into
# a Python script.

from hello3 import HelloInstrument

print( "Instantiatig hello3_main")
hello3_main = HelloInstrument()


print( "\n\nHere follows the output from API calls:")

# This following this line was copy-pasted from the output of examples/hello3/rec.sh (using 
# parameter ='--outputTemplate API')
hello3_main.greet(whom="value entered to first promted value", who="value given to second promted value")
# End of copy-paste


print( "\n\nThats all Folks - Happy coding!!")
