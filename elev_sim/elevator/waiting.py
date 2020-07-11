logging.basicConfig(level=logging.DEBUG)
untilTime = 1000

Dist_InterArrival = './BestFitDistribution.csv'
timeSection = 2
FloorList = ['B4', 'B3', 'B1', '1', '2', '3', '4', '5',
             '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']

# Variable
Ratio_byFloor = ['./FloorRatio_NHB.csv', './FloorRatio_Research.csv',
                 './FloorRatio_SC.csv', './FloorRatio_SHB.csv']
Location = ["北棟病床", "研究大樓", "南棟客梯", "南棟病床"]
# Ratio_byFloor = ['./FloorRatio_NC.csv']
# Location = ["北棟客梯"]
ElevatorList = ['3001', '3002', '3003', '3004', '3005']


for locationI in range(len(Location[:1])):
    Statistic_df = []
    for eleNum in [len(ElevatorList)]:
        #     for i in range(len(ElevatorList)):
        meanStatistic_EleNum = []
        for NumFloor in [len(FloorList)]:
            for j in range(1):
                #                 RandomSeed = int(random.rand(1)*10000)
                RandomSeed = 1234
                # Enviornment Variable
                env = simpy.Environment()
                id_gen = id_generator()

                # Global Event
                CALL_EVENT = env.event()
                RESUBMIT_EVENT = env.event()
                AAA_EVENT = {1: {i: env.event() for i in FloorList[:NumFloor]}, -1: {
                    i: env.event() for i in FloorList[:NumFloor]}}
                BBB_EVENT = {i: env.event() for i in ElevatorList[:eleNum]}
                Mission = namedtuple("Mission", ["direction", "destination"])
                customers_log = []
                elevator_log = []

                # Simulation
                df_result = runElevatorSimulation(
                    Dist_InterArrival, Ratio_byFloor[locationI], Location[locationI], 2, FloorList[:NumFloor], ElevatorList[:eleNum], RandomSeed, CONFIG, NumFloor, untilTime)
                meanStatistic_EleNum.append({'Location': Location[locationI], 'NumFloor': NumFloor, 'Elevator Amount': i+1,
                                             'Waiting_Time': df_result['waiting_time'].mean(), 'Journey_Time': df_result['journey_time'].mean()})

        meanStatistic_EleNum = pd.DataFrame(meanStatistic_EleNum)
#         meanStatistic_EleNum.to_csv(Location[locationI]+'_eachMean.csv')
        Statistic_df.append({'Location': Location[locationI], 'Elevator Amount': i+1, 'Waiting_Time': meanStatistic_EleNum['Waiting_Time'].mean(
        ), 'Journey_Time': meanStatistic_EleNum['Journey_Time'].mean()})
    Statistic_df = pd.DataFrame(Statistic_df)
#     Statistic_df.to_csv(Location[locationI]+'.csv')
