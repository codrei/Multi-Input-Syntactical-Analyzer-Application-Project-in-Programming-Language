// Variables, operators, conditions and loops.
import java.util.Scanner;

public class Basics {
    static final double RATE = 0.05;
    private static int counter = 0;

    public static void main(String[] args) {
        int x = 10, y = 3;
        long big = 10_000_000L;
        float ratio = 1.5f;
        double average = (double) x / y;
        char grade = 'A', newline = '\n', quote = '\'';
        boolean ok = !false && (x > 0 || y < 0);
        int bits = ~x & 0xFF | 0b1010 ^ 017;
        int shifted = x >>> 2;
        String label = x > y ? "bigger" : "smaller";
        var total = x + y * 2 - (x % y);

        if (x > 5) {
            System.out.println("Value is valid");
        } else if (x == 5) {
            System.out.println("Exactly five");
        } else {
            System.out.println("Too small");
        }

        if (ok) counter++; else counter--;

        for (int i = 0; i < 10; i++) {
            if (i % 2 == 0) {
                continue;
            }
            total += i;
        }

        int n = 3;
        while (n > 0) {
            n--;
        }
        do {
            n++;
        } while (n < 3);

        outer:
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 3; col++) {
                if (row * col > 2) break outer;
            }
        }

        for (;;) {
            break;
        }

        switch (grade) {
            case 'A':
                System.out.println("Excellent");
                break;
            case 'B':
            case 'C':
                System.out.println("Good");
                break;
            default:
                System.out.println("Keep going");
        }

        Scanner scanner = new Scanner(System.in);
        System.out.printf("%s %d %.2f%n", label, total, average + RATE + ratio + big + bits + shifted);
        scanner.close();
    }
}
