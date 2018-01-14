/*
 * Copyright (C) The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.android.gms.samples.vision.ocrreader;

import android.content.Context;
import android.os.Handler;
import android.support.design.widget.Snackbar;
import android.util.Log;
import android.util.SparseArray;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.StringRequest;
import com.android.volley.toolbox.Volley;
import com.google.android.gms.samples.vision.ocrreader.ui.camera.GraphicOverlay;
import com.google.android.gms.vision.Detector;
import com.google.android.gms.vision.text.TextBlock;

import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * A very simple Processor which gets detected TextBlocks and adds them to the overlay
 * as OcrGraphics.
 */
public class OcrDetectorProcessor implements Detector.Processor<TextBlock> {
    private String location = "1";

    private Context context;

    private GraphicOverlay<OcrGraphic> mGraphicOverlay;
    private RequestQueue queue;
    private List<String> recentObjects = new ArrayList<>();

    private final Handler handler = new Handler();

    OcrDetectorProcessor(GraphicOverlay<OcrGraphic> ocrGraphicOverlay, Context context) {
        mGraphicOverlay = ocrGraphicOverlay;
        this.context = context;
        // Instantiate the RequestQueue.
        queue = Volley.newRequestQueue(context);
    }

    /**
     * Called by the detector to deliver detection results.
     * If your application called for it, this could be a place to check for
     * equivalent detections by tracking TextBlocks that are similar in location and content from
     * previous frames, or reduce noise by eliminating TextBlocks that have not persisted through
     * multiple detections.
     */
    @Override
    public void receiveDetections(Detector.Detections<TextBlock> detections) {
        mGraphicOverlay.clear();
        SparseArray<TextBlock> items = detections.getDetectedItems();
        for (int i = 0; i < items.size(); ++i) {
            TextBlock item = items.valueAt(i);
            if (item != null && item.getValue() != null) {
                Log.d("OcrDetectorProcessor", "Text detected! " + item.getValue());

                Boolean recentlySeen = false;
                // Don't record the transaction if the object was recently seen.
                for(String obj: recentObjects){
                    if(Objects.equals(obj, item.getValue())){
                        // Recently seen.
                        recentlySeen = true;
                        break;
                    }
                }

                if((item.getValue().length() == 3 || item.getValue().length() == 6)
                        && !recentlySeen) { // Limited to Arizona plates

                    Log.d("recent", "Haven't seen " + item.getValue() + " in a while. Adding.");

                    // Add the object to recently seen and remove it after 2 minutes.
                    recentObjects.add(item.getValue());
                    final String val = item.getValue();
                    handler.postDelayed(new Runnable() {
                        @Override
                        public void run() {
                            for(int i = 0; i < recentObjects.size(); i++) {
                                String obj = recentObjects.get(i);
                                if(Objects.equals(obj, val)) {
                                    Log.d("recent", "It's been a while since seeing " + val + ". Removing");
                                    recentObjects.remove(i);
                                }
                            }
                        }
                    }, 60000);

                    // TODO: Iterate over all nodes.
                    List<String> urls = new ArrayList<>();
                    urls.add("http://18.218.65.69:5000/transactions/new");
                    urls.add("http://54.187.101.231:5000/transactions/new");
                    urls.add("http://34.209.87.124:5000/transactions/new");
//                    String url = "http://18.218.65.69:5000/transactions/new";
//                    String url = "http://34.209.87.124:5000/transactions/new";
//                    String url = ;

                    JSONObject jsonRequest = null;
                    try {
                        jsonRequest = new JSONObject("{\"License\":\"" + item.getValue() +
                                "\",\"Location\":\""+
                                DeviceLocationManager.getInstance().getLocation() + "\"}");
                    } catch (JSONException e) {
                        e.printStackTrace();
                    }
                    for(String url: urls) {
                        // Request a string response from the provided URL.
                        JsonObjectRequest jsonObjectRequest = new JsonObjectRequest(Request.Method.POST, url, jsonRequest,
                                new Response.Listener<JSONObject>() {
                                    @Override
                                    public void onResponse(JSONObject response) {
                                        // Display the first 500 characters of the response string.
                                        Log.d("HTTP", "Response is: " + response.toString());
                                    }
                                }, new Response.ErrorListener() {
                            @Override
                            public void onErrorResponse(VolleyError error) {
                                Log.d("HTTP", "Didn't work" + error);
                            }
                        });
                        // Add the request to the RequestQueue.
                        queue.add(jsonObjectRequest);
                    }
                }
            }
            OcrGraphic graphic = new OcrGraphic(mGraphicOverlay, item);
            mGraphicOverlay.add(graphic);
        }
    }

    /**
     * Frees the resources associated with this detection processor.
     */
    @Override
    public void release() {
        mGraphicOverlay.clear();
    }
}
