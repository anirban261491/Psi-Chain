package com.google.android.gms.samples.vision.ocrreader;

/**
 * Created by jk on 1/13/18.
 */

public class DeviceLocationManager {
    static private DeviceLocationManager inst;
    private String location = "0";

    static DeviceLocationManager getInstance(){
        if(inst == null) {
            inst = new DeviceLocationManager();
        }
        return inst;
    }

    DeviceLocationManager(){}

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }
}
