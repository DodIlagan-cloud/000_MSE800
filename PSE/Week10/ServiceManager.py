class Appointment:
    # Appointment class
    def __init__(self, date, time, service):
        pass


class Service:
    # Service class
    def __init__(self, type):
        pass

    def getType(self):
        return self.type
        
class ServiceManager: 
    def calculateBill(service, hoursWorked):
        rate = 0.0
        if (service.getType().equals("Consultation")):
            rate = 100 # Consultation rate
        elif (service.getType().equals("Surgery")):
            rate = 500 # Surgery rate
        elif (service.getType().equals("Therapy")):
            rate = 150 # Therapy rate
        
        return rate * hoursWorked;
    

    def scheduleAppointment(service, date, time):
        if (service.getType().equals("Consultation")):
            # Logic for scheduling a consultation appointment
            pass
        elif (service.getType().equals("Surgery")):
            # Logic for scheduling a surgery appointment
            pass
        elif (service.getType().equals("Therapy")):
            # Logic for scheduling a therapy appointment
            pass
        # Create and return an appointment
        return Appointment(date, time, service)
    


