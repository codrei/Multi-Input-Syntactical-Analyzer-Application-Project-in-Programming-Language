// Lambdas, streams, anonymous classes, exceptions and text blocks.
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class Functional {
    @FunctionalInterface
    interface Operation {
        int apply(int a, int b);
    }

    static int compute(Operation op, int a, int b) {
        return op.apply(a, b);
    }

    public static void main(String[] args) throws IOException {
        Operation add = (a, b) -> a + b;
        Operation multiply = (a, b) -> {
            int result = a * b;
            return result;
        };
        System.out.println(compute(add, 2, 3) + compute(multiply, 4, 5));

        List<String> names = Arrays.asList("Ada", "Grace", "Linus");
        List<String> longNames = names.stream()
                .filter(name -> name.length() > 3)
                .map(String::toUpperCase)
                .collect(Collectors.toList());
        names.forEach(System.out::println);
        names.forEach(name -> {
            System.out.println(name.charAt(0));
        });

        Runnable task = new Runnable() {
            @Override
            public void run() {
                System.out.println("Running " + longNames.size());
            }
        };
        new Thread(task).start();

        try {
            int value = Integer.parseInt("42");
            assert value > 0 : "value must be positive";
            if (value < 0) {
                throw new IllegalArgumentException("negative");
            }
        } catch (NumberFormatException | ArithmeticException e) {
            System.out.println("Bad number: " + e.getMessage());
        } finally {
            System.out.println("done");
        }

        String text = """
            Hello,
              "text block"
            """;
        char next = (char) ('a' + 1);
        String day = switch (next) {
            case 'a' -> "first";
            default -> "other";
        };
        switch (day) {
            case "first" -> System.out.println(1);
            default -> System.out.println(text + day);
        }
        synchronized (Functional.class) {
            System.out.println(Arrays.toString(new int[] {3, 2, 1}));
        }
    }
}
