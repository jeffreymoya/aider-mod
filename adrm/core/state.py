from transitions import Machine

class InitializationState:
    states = ['idle', 'config_loaded', 'directories_created', 'steps_executed', 'completed']
    
    def __init__(self):
        self.machine = Machine(
            model=self,
            states=InitializationState.states,
            initial='idle'
        )
        self.machine.add_transition('load_config', 'idle', 'config_loaded')
        self.machine.add_transition('create_dirs', 'config_loaded', 'directories_created')
        self.machine.add_transition('execute_steps', 'directories_created', 'steps_executed')
        self.machine.add_transition('complete', 'steps_executed', 'completed') 