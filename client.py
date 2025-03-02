import grpc
import random
import time
import threading
import sys
import water_quality_pb2
import water_quality_pb2_grpc

class WaterMonitoringStation:

    def __init__(self, station_id, server_address):
        self.station_id = station_id
        self.server_address = server_address
        self.sensors = []  # List of Sensor objects
        self.channel = grpc.insecure_channel(server_address)
        self.stub = water_quality_pb2_grpc.WaterControlCenterStub(self.channel)
        self.stopping = False

        # Register the station with the server
        self.register_station()

    def register_station(self):
        request = water_quality_pb2.RegisterStationRequest(station_id=self.station_id)
        try:
            response = self.stub.RegisterStation(request)
            print(response.message)
        except grpc.RpcError as e:
            print(f"Error registering station: {e}")

    def add_neighbour(self, neighbour_id):
        request = water_quality_pb2.AddNeighbourRequest(station_id=self.station_id, neighbour_id=neighbour_id)
        try:
            response = self.stub.AddNeighbour(request)
            print(f"Neighbour added: {response.message}")
        except grpc.RpcError as e:
            print(f"Error adding neighbour: {e}")

    def simulate_sensors(self):
        while not self.stopping:
            threads = []
            for sensor in self.sensors:
                thread = threading.Thread(target=sensor.check_contaminants)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            time.sleep(5)

    def stop(self):
        self.stopping = True

class Sensor:

    def __init__(self, sensor_id, station):
        self.sensor_id = sensor_id
        self.station = station
        self.pH, self.turbidity, self.pollutants = self.get_sensor_data()

    def get_sensor_data(self):
        return random.uniform(6.0, 8.5), random.uniform(0, 10), random.uniform(0, 100)

    def check_contaminants(self):
        self.pH, self.turbidity, self.pollutants = self.get_sensor_data()
        if self.pollutants > 90:  
            issue_type = "Pollution detected"
            print(f"Issue detected by Sensor {self.sensor_id}: {issue_type}")
            self.report_issue(issue_type)
        if self.pH < 6 or self.pH > 8:
            issue_type = "pH imbalance detected"
            print(f"Issue detected by Sensor {self.sensor_id}: {issue_type}")
            self.report_issue(issue_type)
        if self.turbidity > 9:
            issue_type = "Turbulance detected"
            print(f"Issue detected by Sensor {self.sensor_id}: {issue_type}")
            self.report_issue(issue_type)

    def report_issue(self, issue_type):
        request = water_quality_pb2.IssueReport(station_id=self.station.station_id, issue_type=issue_type, timestamp=time.time())
        try:
            response = self.station.stub.ReportIssue(request)
            print(f"Issue reported: {response.message}")
        except grpc.RpcError as e:
            print(f"Error reporting issue: {e}")

    def print_data(self):
        pH, turbidity, pollutants = self.get_sensor_data()
        request = water_quality_pb2.StationRequest(station_id=self.station_id)
        try:
            response = self.stub.GetQualityData(request)
            print(f"Data for {self.station_id}: pH={response.pH}, turbidity={response.turbidity}, pollutants={response.pollutants}")
        except grpc.RpcError as e:
            print(f"Error fetching data: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python client.py <station_id>")
        sys.exit(1)
    
    station_id = sys.argv[1]
    station = WaterMonitoringStation(station_id, "localhost:50051")
    station.sensors.append(Sensor("Sensor1", station))
    station.sensors.append(Sensor("Sensor2", station))
    
    #station.add_neighbour("Station2")
    #station.add_neighbour("Station3")

    # Start the simulation in separate threads
    sensor_thread = threading.Thread(target=station.simulate_sensors)

    sensor_thread.start()

    # Gracefully handle Ctrl+C (KeyboardInterrupt)
    try:
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nStopping client execution gracefully...")
        station.stop()  # Stop the sensor simulation and reporting
        sensor_thread.join()  # Ensure the sensor thread finishes
        print("Client execution stopped.")

if __name__ == "__main__":
    main()
