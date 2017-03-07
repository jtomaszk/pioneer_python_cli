commands = {
    # response: [name, query]
    'ATW': ['LOUDNESS', '?V'],
    'VOL': ['VOLUME', '?V'],
    'ATC': ['EQ'],
    'ATD': ['STANDING_WAVE'],
    'PWR': ['POWER', '?P'],
    'MUT': ['MUTE', '?M'],
    'FN': ['INPUT', '?F'],
    'SR': ['LISTENING_MODE', '?S'],
    'LM': ['PLAYING_LISTENING_MODE', '?L'],
    'FR': ['TUNER_FRQ', '?FR'],
    'PRA': ['TUNER_PRESENT', '?PR']
}

response_on_off = {
    'ATW',
    'ATC',
    'PWR',
    'MUT',
    'ATD'
}
