package com.example.shop;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;

/**
 * Exercises Inventory methods to produce log output for RAG testing.
 */
public class RunInventory {

    private static final DateTimeFormatter FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private static void log(String level, String msg) {
        System.out.printf("%s %-8s %s%n", LocalDateTime.now().format(FMT), level, msg);
    }

    public static void main(String[] args) {
        log("INFO", "Starting Java inventory scenario");

        Inventory inv = new Inventory();

        // --- addStock ---
        inv.addStock("Widget", 50);
        log("INFO", "addStock: product=Widget quantity=50 stock=" + inv.getStock("Widget"));

        inv.addStock("Gadget", 20);
        log("INFO", "addStock: product=Gadget quantity=20 stock=" + inv.getStock("Gadget"));

        // --- reserveStock: success ---
        try {
            inv.reserveStock("Widget", 10);
            log("INFO", "reserveStock: product=Widget reserved=10 remaining=" + inv.getStock("Widget"));
        } catch (IllegalStateException e) {
            log("ERROR", "reserveStock failed: " + e.getMessage());
            e.printStackTrace(System.out);
        }

        // --- reserveStock: failure (requested 25 > available 20) ---
        try {
            inv.reserveStock("Gadget", 25);
            log("INFO", "reserveStock: product=Gadget reserved=25 remaining=" + inv.getStock("Gadget"));
        } catch (IllegalStateException e) {
            log("ERROR", "IllegalStateException: " + e.getMessage());
            e.printStackTrace(System.out);
        }

        // --- calculateInventoryValue: success ---
        Map<String, Double> prices = new HashMap<>();
        prices.put("Widget", 9.99);
        prices.put("Gadget", 49.99);
        try {
            double total = inv.calculateInventoryValue(prices);
            log("INFO", String.format("calculateInventoryValue: total=%.2f", total));
        } catch (IllegalArgumentException e) {
            log("ERROR", "IllegalArgumentException: " + e.getMessage());
            e.printStackTrace(System.out);
        }

        // --- calculateInventoryValue: missing price triggers IllegalArgumentException ---
        inv.addStock("Sprocket", 5);
        log("INFO", "addStock: product=Sprocket quantity=5 stock=" + inv.getStock("Sprocket"));

        Map<String, Double> incompletePrices = new HashMap<>();
        incompletePrices.put("Widget", 9.99);
        incompletePrices.put("Gadget", 49.99);
        // Sprocket has no price — will throw IllegalArgumentException
        try {
            double total = inv.calculateInventoryValue(incompletePrices);
            log("INFO", String.format("calculateInventoryValue: total=%.2f", total));
        } catch (IllegalArgumentException e) {
            log("ERROR", "IllegalArgumentException: " + e.getMessage());
            e.printStackTrace(System.out);
        }

        log("INFO", "Java inventory scenario complete");
    }
}
