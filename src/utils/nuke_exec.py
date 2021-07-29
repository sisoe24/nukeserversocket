def _pyscript_knob(msg):
    # This seems to work fine but does not return anything
    cmd = nuke.PyScript_Knob('exec', 'Execute', msg.data().decode('utf-8'))
    cmd.execute()


def _execute_main():
    # This should be the method by needs more time to investigate
    cmd = nuke.executeInMainThreadWithReturn()
