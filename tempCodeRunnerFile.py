 threading.Thread(
        target=update_time, args=[stop_ev, message_q],
        name='update_time',
    ).start()