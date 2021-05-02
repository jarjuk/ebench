# api-demo.py - tangled from GENTLE_SLOPE.org to demonstrate 
# an idea, how the interactive recording can be turned into
# a Python script.

from hello2 import HelloInstrument

print( "Instantiatig HelloInstrument as hello2_main")
hello2_main = HelloInstrument()


print( "\n\nHere follows the output from API calls:")

# This following this line was copy-pasted from the output of examples/hello2-api/rec.sh (using 
# parameter ='--outputTemplate API')
hello2_main.sayHello(whom="value entered to first promted value", who="value given to second promted value")
# End of copy-paste


print( "\n\nThats all Folks - Happy coding!!")
