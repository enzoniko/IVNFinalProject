#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <inet/common/ModuleAccess.h>
#include <inet/common/TimeTag_m.h>
#include "apps/alert/AlertSender.h"

Define_Module(AlertSender);

using namespace inet;

AlertSender::AlertSender() {
    selfSender_ = nullptr;
    nextSno_ = 0;
}

AlertSender::~AlertSender() {
    cancelAndDelete(selfSender_);
}

void AlertSender::initialize(int stage) {
    if (stage != inet::INITSTAGE_APPLICATION_LAYER)
        return;

    EV << "AlertSender::initialize - stage " << stage << endl;

    selfSender_ = new cMessage("selfSender");

    // Retrieve vehicle ID and prepare file path
    std::string vehicleName = getParentModule()->getFullName(); // Assuming vehicle name contains ID
    std::string vehicleId = vehicleName.substr(vehicleName.find('[') + 1, vehicleName.find(']') - vehicleName.find('[') - 1);
    std::string filePath = std::string("vehiclesCAMs/vehicle_") + vehicleId + ".csv";
    std::cout << filePath << endl;

    EV << "Loading CSV for vehicle: " << vehicleId << ", path: " << filePath << endl;

    // Load CSV file
    if (!loadCsvFile(filePath)) {
        throw cRuntimeError("Failed to load CSV file: %s", filePath.c_str());
    }

    // Socket initialization
    localPort_ = par("localPort");
    destPort_ = par("destPort");
    destAddress_ = inet::L3AddressResolver().resolve(par("destAddress").stringValue());

    socket.setOutputGate(gate("socketOut"));
    socket.bind(localPort_);

    int tos = par("tos");
    if (tos != -1)
        socket.setTos(tos);

    // Multicast support
    inet::IInterfaceTable *ift = inet::getModuleFromPar<inet::IInterfaceTable>(par("interfaceTableModule"), this);
    inet::MulticastGroupList mgl = ift->collectMulticastGroups();
    socket.joinLocalMulticastGroups(mgl);

    const char *multicastInterface = par("multicastInterface");
    if (multicastInterface[0]) {
        NetworkInterface *ie = ift->findInterfaceByName(multicastInterface);
        if (!ie)
            throw cRuntimeError("Wrong multicastInterface setting: no interface named \"%s\"", multicastInterface);
        socket.setMulticastOutputInterface(ie->getInterfaceId());
    }

    // Schedule the first message
    if (!timestamps_.empty()) {
        scheduleAt(timestamps_[0], selfSender_);
    } else {
        EV << "No messages to send for vehicle: " << vehicleId << endl;
    }
}

bool AlertSender::loadCsvFile(const std::string &filePath) {
    std::ifstream file(filePath);
    if (!file.is_open())
        return false;

    std::string line;
    while (std::getline(file, line)) {
        std::istringstream ss(line);
        std::string timestampStr, sizeStr;

        if (std::getline(ss, timestampStr, ',') && std::getline(ss, sizeStr)) {
            simtime_t timestamp = std::stod(timestampStr);
            int size = std::stoi(sizeStr);

            timestamps_.push_back(timestamp);
            sizes_.push_back(size);
        }
    }

    file.close();
    return true;
}

void AlertSender::handleMessage(cMessage *msg) {
    if (msg == selfSender_) {
        sendAlertPacket();
    } else {
        //throw cRuntimeError("Unexpected message received");
        std::cout << "Unexpected message received!" << endl;
    }
}

void AlertSender::sendAlertPacket() {
    if (nextSno_ >= timestamps_.size()) {
        EV << "No more messages to send" << endl;
        return;
    }

    // Create and send packet
    Packet *packet = new Packet("VehicleCAM");
    auto alert = makeShared<AlertPacket>();

    alert->setSno(nextSno_);
    alert->setPayloadTimestamp(simTime());
    alert->setChunkLength(B(sizes_[nextSno_]));
    alert->addTag<CreationTimeTag>()->setCreationTime(simTime());
    packet->insertAtBack(alert);

    socket.sendTo(packet, destAddress_, destPort_);

    const char* nodename = getParentModule()->getFullName();
    getParentModule()->getName();
    std::cout << "NODE NAME: " << nodename << std::endl;
    std::cout << "Timestamp: " << simTime() << " Size: " << sizes_[nextSno_] << std::endl;
    std::cout << "Packet Size: " << packet-> getByteLength() << " Dest Address: " << destAddress_ << " Dest Port: " << destPort_ << endl;

    nextSno_++;

    // Schedule next message
    if (nextSno_ < timestamps_.size()) {
        scheduleAt(timestamps_[nextSno_], selfSender_);
    }
}

void AlertSender::refreshDisplay() const {
    char buf[80];
    sprintf(buf, "sent: %d pks", nextSno_);
    getDisplayString().setTagArg("t", 0, buf);
}
