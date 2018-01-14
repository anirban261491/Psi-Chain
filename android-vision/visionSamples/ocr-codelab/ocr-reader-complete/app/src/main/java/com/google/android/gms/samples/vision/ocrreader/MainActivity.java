package com.google.android.gms.samples.vision.ocrreader;

import android.content.Intent;
import android.support.design.widget.Snackbar;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        final EditText editText = (EditText) findViewById(R.id.edittext);
        Button goButton = (Button) findViewById(R.id.button);
        goButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                DeviceLocationManager.getInstance().setLocation(editText.getText().toString());
//                Toast.makeText(MainActivity.this, String.format("Sending from location %s", editText.getText().toString()), Toast.LENGTH_LONG).show();
                startActivity(new Intent(MainActivity.this, OcrCaptureActivity.class));
            }
        });

    }
}
