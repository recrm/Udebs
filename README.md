Udebs: A descrete game battle system for python3.

Udebs is an experiment in python game mechanics engines. I started working on project while I was first learning python. Origionally I just wanted to make a basic old school style rpg battle game; however, I soon found that making the engine itself was quite a bit more fun then making the whole game (I'm a good programmer, but not that great at the rest of game design). What resulted is the udebs battle system.

My goal for this document is to share as best as I can the experiment that is udebs. Because it did not originate out of any practical considerations I can't speak for the usefullness of this project. I hope its useful, but in its current form it has not been tested against any major projects. I would really like to change that, but until udebs can be worked to fit an actual project it will simply remain an experiment.

As this project had no real solid direction at its inception, and it has gone through way to many complete overhauls to date, there is no real documentation for this project. I hope to fix this in the future, but for now I thought it would be best to put together a quick tutorial describing how to use this project.

Hello World for udebs.

To start let's throw together a quick hello world script.

    import udebs

    config = """
    <udebs>
        <entities>
            <hello>
                <effect>print Hello World!!!!</effect>
            </hello>
        </entities>
    </udebs>
    """

    world = udebs.battleStart(config)
    game.controlInit("hello")

Every udebs program can be divided into two distinct parts. The udebs configuration script which is written in xml (A choice I do not regret.) and the proper python3 script. The udebs configuration file itself breaks down into a number of nodes. The most important node, and the only one in this example, is the 'entities' node which will contain all of the events in our system.

You will notice that when you run this script the string "Hello World!!!!" will be printed to the terminal along with a bunch of other stuff. By default, udebs logs everything it does to the terminal. This is a great tool for debuging as well as a convenient teaching tool to get an understanding of how the engine thinks. However, if you want to turn it off you can simply add <config><logging>False</logging></config> as a sibling to entities.

The rest of the script is fairly self explanitory. The first function (udebs.battleStart) is a parseing function that takes a string (or a path to a file) and returns an object of class 'udebs.instance'. This object represents the current state space of the entire engine. The final function (instance.controlInit) simply triggers the 'hello' event.

Before going into detail about the udebs scripting language that allows this all to work let's take a look at a slightly more complicated example.

Udebs Rock Paper Scissors.

    import udebs

    xml = """
    <udebs>
    <definitions>
        <strings>
            <beats />
        </strings>
    </definitions>

    <entities>
        <rps>
            <effect>
                <i>winner =
                    (if ($target == (STAT $caster beats))
                        $caster
                        $target)
                </i>

                <i>print $winner wins!!</i>
            </effect>
        </rps>
        <rock>
            <beats>scissors</beats>
        </rock>
        <paper>
            <beats>rock</beats>
        </paper>
        <scissors>
            <beats>paper</beats>
        </scissors>
    </entities>

    </udebs>
    """

    game = udebs.battleStart(xml)

    player_choice = input("What will you play? ")
    cpu_choice = "rock"

    game.controlMove(player_choice, cpu_choice, "rps")

The above script has bugs in it, but we will fix them in a moment. For now run it and when asked supply the input with either 'paper' or 'scissors'. Afterwords it should gleefully tell you which choice has won the round.

In udebs all actions are 'directed' which means that every action is initiated by some object and recived by some other object. In the above example the function instance.controlInit has been replaced with instance.controlMove and given three arguments: two actors, and the event itself. Each of the actors are passed to the event as the variables $caster and $target (first argument being $caster second being $target).

Just like in the hello world example the controlMove function activates the 'rps' event object. The triggered event then activates each of it's effect subnodes in the order that they are written. The first effect chooses which object is the winner, while the second prints it to the screen. As you may notice the hello world script does not implement the i tag. This is just shorthand. If the parser finds no i nodes in the effects node. It simply takes the text of that node as its one and only effect.

Let's take a closer look at the print function.

    <i>print $winner wins!!!</i>

Every udebs effect object gets compiled into a single function call. In this case it gets compiled to the python3 print function.

    print(winner, "wins!!!")

udebs searches every effect object for a keyword. Once found every other empty-space delimited entry is treated as a argument to that function based on its position. As with all other programing languages, if the return of one function becomes the argument of another we can surround it with brackets.

    <i>winner = (if-statement)</i>

That is the value returned by the if statement is assigned to the variable $winner. In fact, this effect has four different keywords in it (=, ==, if, STAT) each existing by itself in its own bracketed universe. (The compiler will error if it detects more than one keyword in a function call.)

Anyone familiar with Lisp type languages should recognize the if construct. This is because the udebs scripting language is heavily influenced by Lisp. In standard Lisp programming language each function call is in fact a list: (keyword argument1 argument2 ...) Udebs changes this formula a little bit by not requiring that the keyword be at the front of the list. This allows for more natural constructions like (1 + 1) instead of the Lisp standard (+ 1 1). Other important things to note is that variables are explicitly marked ($winner instead of just winner) this is because the config file is read first by an XML parser and therfore everything is already a string. (Note: the if construct is very broken. Both of the if and else clauses are processed every time. Only the correct clause is returned. I'm not activly working on this right now, so it is unlikely to get fixed.)

I need to repeat that. In udebs scripting EVERYTHING is a string unless it explicitly is not. In this case the variables are marked in order to tell interpreter that it is indeed a variable and not just a string (the marking is actually a function call on a string, but we will get into that later). Keywords are also strings, however, they are special strings that the interpreter singles out after the xml parser is done with the config file. This is also true of event objects. An event object is represented by the string that defines it. So in all cases the string 'rock' will be interpreted as a reference to the event 'rock' defined in entities. There is more to say about udebs function calls but we will have to return to that topic a bit later. (Yes, there are a ton of namespace issues here. Hence my frequent use of the word "experimental".)

There is a second thing happening in this script. Events now have attributes. As all events inherit from the same object thay all have the same attributes. New attributes need to be defined in the 'definitions' node. Likewise, all attributes have a type. Udebs distinguishes between three different types of attributes: lists, strings, and stats (integers). The majority of the differences between these should be obvious, so we will skip over the topic for now. For now all that is important is that the keyword 'STAT' is a getter function. In this case it gets the 'beats' attribute from $caster.

A better Udebs Rock Paper Scissors game.

As I said above the Rock Paper Scissors script is broken. Below is a fixed version of the above script.

    import udebs

    xml = """
    <udebs>

    <definitions>
        <strings>
            <beats />
        </strings>
    </definitions>

    <config>
        <logging>False</logging>
    </config>

    <entities>
        <rps>
            <require>
                <i>action in (STAT $target group)</i>
                <i>action in (STAT $caster group)</i>
            </require>

            <effect>
                <i>winner =
                    (if ($target == STAT.$caster.beats) $caster $target)
                </i>

                <i>winner =
                    (if ($target == $caster) ties $winner)
                </i>

                <i>print $winner wins!!</i>
            </effect>
        </rps>

        <rock>
            <beats>scissors</beats>
            <group>action</group>
        </rock>

        <paper>
            <beats>rock</beats>
            <group>action</group>
        </paper>

        <scissors>
            <beats>paper</beats>
            <group>action</group>
        </scissors>

        <action />
    </entities>

    </udebs>
    """

    game = udebs.battleStart(xml)
    cpu_choice = "rock"

    player_choice = input("What will you play? ")
    while player_choice not in game.getGroup('action'):
        player_choice = input("That is not a valid action. Try again. ")

    game.controlMove(player_choice, cpu_choice, "rps"):

Many things going on here. First thing is that I have turned logging off. As I worked on this I got annoyed at all of the extra text the engine was flashing to the screen. Similarily, there are several other engine modifications that can be tweeked in a similar fashion using the config node. Secondly I have added several conditions onto the rps event. Whenever an event triggers the engine first checks it's 'require' attribute. All events in the require attribute must be true before an event can trigger. Here, both the $caster and the $target must be in the 'action' group. Unfortunatly, this fix is simply here as an example. These restriction alone would not fix the KeyError bug because the user might still try to launch an undefined event. As a more permanent solution I am also manually checking to see if the user's input is in the 'action' group manually. However, if switched the cpu_choice to say 'rps' (a defined event not in the 'action' group) then the even will not trigger and nothing will be printed.

As you might have noticed, we did not define either of the 'require' or 'group' attributes. That is because these attributes are hardcoded into engine and are always available (The complete list of hardcoded attributes: effect (list), require (list), group (list), increment (stat)). Group is a special list attribute (similar to effect) that contains references to other events. This is why there is now an empty <action /> node in entities. All groups must be references to other event objects. We will see why in the next and last example.

An unneccessarily complicated Rock Paper Scissors game.

The final example can be found in RPS.py. I have tried to put all of the basic elements of udebs together. There is most certainly better and more compact ways to implment what I have done here, but the convoluted nature is designed to demonstrate all aspects of the engine and not to demonstrate the best way to actually implement a game of rock paper scissors.

Several things to note here.

The events 'user' and 'computer' are inheriting two lives from their class. Instead of choosing manually what moves each player makes, we have implemented a custom 'CHOICE' function that does it for us. The function udebs.importModule is used to import custom functions into the udebs engine.

There are plenty more argument types that can be put into a custom function, but I only recommend positional arguments for now.

Unfortunatly, this is all I have time for. Udebs is currently only in version 1 and has a ton of rough edges. If you have any questions please take a look at the three examples bundled with this software (river.py, chess.py, hex.py). If you are not comfortable looking at raw python code in order to figure out how things work then this project is probobly not for you yet. Thanks for the read.
