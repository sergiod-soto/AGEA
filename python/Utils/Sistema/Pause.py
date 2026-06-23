def pause(shared_data):

    # Auxiliares: resumir
    def resumeAux(shared_data):
        print("resumiendo")
        shared_data["other"]["paused"] = False

    # Auxiliares: pausar
    def pauseAux(shared_data):
        print("pausando")
        shared_data["other"]["paused"] = True

    if shared_data["other"]["paused"]:
        resumeAux(shared_data)
        return
    pauseAux(shared_data)
