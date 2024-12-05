#ifndef _LTE_ALERTSENDER_H_
#define _LTE_ALERTSENDER_H_

#include <string.h>
#include <omnetpp.h>
#include <inet/transportlayer/contract/udp/UdpSocket.h>
#include <inet/networklayer/common/L3Address.h>
#include <inet/networklayer/common/L3AddressResolver.h>
#include "apps/alert/AlertPacket_m.h"

#include <fstream> // For file I/O
#include <vector>  // For storing timestamps and sizes

class AlertSender : public omnetpp::cSimpleModule
{
    inet::UdpSocket socket;

    //sender
    int nextSno_;
    std::vector<omnetpp::simtime_t> timestamps_; // Store timestamps from the CSV
    std::vector<int> sizes_;            // Store sizes from the CSV

    omnetpp::simtime_t stopTime_;

    omnetpp::simsignal_t alertSentMsg_;
    // ----------------------------

    omnetpp::cMessage *selfSender_;

    int localPort_;
    int destPort_;
    inet::L3Address destAddress_;

    void sendAlertPacket();

    // Helper methods
    bool loadCsvFile(const std::string & filepath);  // Load the CSV file
    void scheduleNextMessage(); // Schedule based on timestamps

  public:
    ~AlertSender();
    AlertSender();

  protected:
    virtual int numInitStages() const override { return inet::NUM_INIT_STAGES; }
    void initialize(int stage) override;
    void handleMessage(omnetpp::cMessage *msg) override;

    // utility: show current statistics above the icon
    virtual void refreshDisplay() const override;
};

#endif
