//
//                  Simu5G
//
// Authors: Giovanni Nardini, Giovanni Stea, Antonio Virdis (University of Pisa)
//
// This file is part of a software released under the license included in file
// "license.pdf". Please read LICENSE and README files before using it.
// The above files and the present reference are part of the software itself,
// and cannot be removed from it.
//
package simu5g.simulations.NR.carsLuST;

import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.networklayer.ipv4.RoutingTableRecorder;
import inet.node.inet.AdhocHost;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import inet.node.ethernet.Eth10G;

import simu5g.world.radio.LteChannelControl;
import simu5g.common.carrierAggregation.CarrierAggregation;
import simu5g.nodes.Upf;
import simu5g.common.binder.Binder;
import simu5g.nodes.NR.gNodeB;
import simu5g.nodes.backgroundCell.BackgroundCell;
import simu5g.nodes.cars.NRCar;
import simu5g.nodes.NR.NRUe;

import org.car2x.veins.subprojects.veins_inet.VeinsInetManager;

network FiveGWorld
{
    parameters:
        double playgroundSizeX @unit(m) = default(1500m); // x size of the area the nodes are in (in meters)
        double playgroundSizeY @unit(m) = default(1500m); // y size of the area the nodes are in (in meters)
        double playgroundSizeZ @unit(m) = default(50m); // z size of the area the nodes are in (in meters)
        int numGNodeBs = default(1); // Number of gNodeBs in the simulation
        int numBgCells = default(0); // Number of background cells in the simulation
        int numUes = default(0); // Number of UEs in the simulation (besides cars)
        int numBgUes = default(0); // Number of background UEs in the simulation
        int numCars = default(10000);
        @display("bgb=732,483");

    submodules:

        routingRecorder: RoutingTableRecorder {
            @display("p=50,75;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=50,125");
            config = xmldoc("demo.xml");
        }

        // # Veins manager module
        veinsManager: VeinsInetManager {
            @display("p=50,227;is=s");
        }

        // # LTE modules
        channelControl: LteChannelControl {
            @display("p=50,25;is=s");
        }
        binder: Binder {
            @display("p=50,175;is=s");
        }
        carrierAggregation: CarrierAggregation {
            @display("p=50.993748,258.7;is=s");
        }
        server: StandardHost {
            @display("p=660,136;is=n;i=device/server");
        }
        router: Router {
            @display("p=561,135;i=device/smallrouter");
        }
        upf: Upf {
            @display("p=462,136");
        }
        
        gNodeB[numGNodeBs]: gNodeB {
            parameters:
                mobility.initFromDisplayString = false;
                macNodeId = default(index + 1);
                macCellId = default(index + 1);
            //@display("p=416,277");
        } // Dynamic gNodeB array
        
        bgCell[numBgCells]: BackgroundCell;
	
		// This is problematic, because we need to define the master and which cells they connect
		//ue[numUes]: NRUe {
        //    @display("p=499.056,428.244");
        //    parameters:
        //        masterId
        //}
        
        // # submodule vector to store all cars - will be filled dynamically during simulations
        car[0]: NRCar;

    connections allowunconnected:
        server.pppg++ <--> Eth10G <--> router.pppg++;
        router.pppg++ <--> Eth10G <--> upf.filterGate;

        // Connect UPF to each gNodeB
        for i=0..sizeof(gNodeB)-1 {
            upf.pppg++ <--> Eth10G <--> gNodeB[i].ppp; 
        }

        // X2 connections between gNodeBs
        for i=0..sizeof(gNodeB)-2 {
            
            gNodeB[i].x2++ <--> Eth10G <--> gNodeB[i+1].x2++;
            
        }
        
        gNodeB[sizeof(gNodeB)-1].x2++ <--> Eth10G <--> gNodeB[0].x2++; // Connect the last one with the first one
}