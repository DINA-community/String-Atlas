# Use Cases Global

# Token mit gleichen Prefix unterscheidet zwischen Serie
SIMATIC -> Brand

S7-700, S7-400 -> Serie/Generation, Subserie
S7-PM -> Serie -> Komponente
S7-PCSLM -> Software


# Schreibweisen


# Wortpositionen von Features
PN/XX -> Varianten ermitteln nach Special Char, Prefix und wenigen Varianten des Suffix
SIMATIC PN/PN Coupler
SIMATIC ET 200pro IM154-8 PN/DP CPU (6ES7154-8AB01-0AB0)


# Whitespaces schreibweisen > ET 200pro . segmentvergleich und vorher whitespaces Strippen bei unterschiedlichen segmenttypen der Token
SIMATIC ET 200pro IM154-8 PN/DP CPU (6ES7154-8AB01-0AB0)
['ET', '200', '^[A-Za-z]+$']






Gruppierung von Tolen über self.group_token bei SIMATIC Brand
-> es passt nur software nicht
-> generisches regex wurde generiert -> hier die unterserie 180(C), 166(C) usw. extrhahieren

['S7-300', 'S7-400', 'S7-200', 'S7-1500']
['ET200SP', 'ET200MP', 'ET200AL', 'ET200M', 'ET200S', 'ET200pro', 'ET200pro,', 'ET200ecoPN,']
['S7-PM', 'S7-PLCSIM']
['IPC427E', 'IPC647E', 'IPC847E', 'IPC627E', 'IPC677E', 'IPC477D', 'IPC547E', 'IPC127E', 'IPC1047E', 'IPC227E', 'IPC277E', 'IPC347E', 'IPC477E']
['RF185C', 'RF186C', 'RF182C', 'RF188CI', 'RF180C', 'RF166C', 'RF188C']
['PN/MF', 'PN/PN']
['IPC527G', 'IPC547D', 'IPC347G', 'IPC547G']
['IPC847D', 'IPC677D', 'IPC627D', 'IPC827D', 'IPC427D', 'IPC647C', 'IPC647D']
['RF680R', 'RF685R', 'RF650M', 'RF615R', 'RF360R', 'RF610R', 'RF650R']
['RTU3030C', 'RTU3031C', 'RTU3041C', 'RTU3010C']
['IPC847C', 'IPC827C', 'IPC627C']