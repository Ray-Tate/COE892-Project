import grpc
from concurrent import futures
import time
import water_quality_pb2
import water_quality_pb2_grpc

class WaterControlCenterServicer(water_quality_pb2_grpc.WaterControlCenterServicer):

    def __init__(self):
        self.stations = {}  # {station_id: (pH, turbidity, pollutants)}
        self.neighbours = {}  # {station_id: [neighbour_station_ids]}

    def GetQualityData(self, request, context):
        station_id = request.station_id
        if station_id in self.stations:
            pH, turbidity, pollutants = self.stations[station_id]
            return water_quality_pb2.StationResponse(station_id=station_id, pH=pH, turbidity=turbidity, pollutants=pollutants)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f'Station {station_id} not found')
            return water_quality_pb2.StationResponse()

    def ReportIssue(self, request, context):
        station_id = request.station_id
        issue_type = request.issue_type
        timestamp = request.timestamp
        self.NotifyNeighbours(station_id, issue_type)
        return water_quality_pb2.StatusResponse(message=f"Issue reported: {issue_type} at {station_id}", success=True)

    def NotifyNeighbours(self, station_id, issue_type):
        if station_id in self.neighbours:
            for neighbour_id in self.neighbours[station_id]:
                print(f"Notifying {neighbour_id} about issue: {issue_type}")
                request = water_quality_pb2.NeighbourNotification(station_id=station_id, issue_type=issue_type)
                # Here you would make an RPC call to the neighbour stations (simulated here)
                # Example: self.stub.NotifyNeighbours(request)

    def AddNeighbour(self, request, context):
        station_id = request.station_id
        neighbour_id = request.neighbour_id

        if station_id not in self.neighbours:
            self.neighbours[station_id] = []
        if neighbour_id not in self.neighbours:
            self.neighbours[neighbour_id] = []

        if neighbour_id not in self.neighbours[station_id]:
            self.neighbours[station_id].append(neighbour_id)
        if station_id not in self.neighbours[neighbour_id]:
            self.neighbours[neighbour_id].append(station_id)

        return water_quality_pb2.StatusResponse(message=f"{station_id} and {neighbour_id} are now neighbours.", success=True)

    def RegisterStation(self, request, context):
        station_id = request.station_id
        if station_id not in self.stations:
            self.stations[station_id] = (7.0, 5.0, 0.0)  # Default values for pH, turbidity, pollutants
            return water_quality_pb2.RegisterStationResponse(message=f"Station {station_id} registered successfully.", success=True)
        else:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(f"Station {station_id} already registered.")
            return water_quality_pb2.RegisterStationResponse(message=f"Station {station_id} already exists.", success=False)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    water_quality_pb2_grpc.add_WaterControlCenterServicer_to_server(WaterControlCenterServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Server started at [::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
