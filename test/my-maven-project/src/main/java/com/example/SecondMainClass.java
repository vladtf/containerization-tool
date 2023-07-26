package com.example;

public class SecondMainClass {

    public static void main(String[] args) {
        while (true) {
            System.out.println("Hello World!");
            try {
                // Pause the loop for 3 seconds
                Thread.sleep(3000);
            } catch (InterruptedException e) {
                System.out.println("Thread interrupted: " + e.getMessage());
            }
        }
    }
}
