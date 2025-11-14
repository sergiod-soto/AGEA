

def pause(shared_data):

    # Auxiliares: resumir
    def resumeAux(shared_data):
        shared_data["other"]["paused"] = False

    # Auxiliares: pausar
    def pauseAux(shared_data):
        shared_data["other"]["paused"] = True

    if shared_data["other"]["paused"]:
        resumeAux(shared_data)
        return
    pauseAux(shared_data)
