package com.example.shop;

import java.util.HashMap;
import java.util.Map;

/**
 * Manages product inventory for the shop.
 */
public class Inventory {

    private Map<String, Integer> stock = new HashMap<>();

    public void addStock(String product, int quantity) {
        stock.merge(product, quantity, Integer::sum);
    }

    public int getStock(String product) {
        return stock.getOrDefault(product, 0);
    }

    public void reserveStock(String product, int quantity) {
        int current = getStock(product);
        if (current < quantity) {
            throw new IllegalStateException(
                "Insufficient stock for " + product + ": requested=" + quantity + " available=" + current
            );
        }
        stock.put(product, current - quantity);
    }

    public double calculateInventoryValue(Map<String, Double> prices) {
        double total = 0.0;
        for (Map.Entry<String, Integer> entry : stock.entrySet()) {
            Double price = prices.get(entry.getKey());
            if (price == null) {
                throw new IllegalArgumentException("No price found for product: " + entry.getKey());
            }
            total += price * entry.getValue();
        }
        return total;
    }
}
