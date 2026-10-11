import java.io.BufferedReader;
import java.io.IOException;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;

public class Layouts
{
    enum Planet
    {
        MERCURY(3.3),
        VENUS(4.8);

        private final double mass;

        Planet(double mass)
        {
            this.mass = mass;
        }
    }

    enum Level {
        LOW,
        MEDIUM,
        HIGH
    }

    interface Greeter {
        String greet(String name);

        default String hello()
        {
            return greet("world");
        }
    }

    private static int counter;

    static {
        counter = 1;
    }

    static String read(String text)
        throws IOException
    {
        try (BufferedReader reader = new BufferedReader(new StringReader(text))) {
            return reader.readLine();
        }
    }

    static <T> List<T> twice(T value)
    {
        List<T> list = new ArrayList<>();
        list.add(value);
        list.add(value);
        return list;
    }

    public static void main(String[] args) throws IOException
    {
        int total = 0;
        String label = "a"
            + "b"
            + "c";
        int max = total > 5
            ? total
            : 5;
        Greeter greeter = new Greeter() {
            @Override
            public String greet(String name) {
                return "Hi " + name;
            }
        };
        Function<Integer, Integer> square = x -> x * x;
        Level level = Level.HIGH;
        String size = switch (level) {
            case LOW -> "small";
            case MEDIUM -> "medium";
            default -> "large";
        };
        StringBuilder builder = new StringBuilder()
            .append(label)
            .append(max);

        outer:
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                if (i * j > 2) {
                    break outer;
                }
                total += square.apply(j);
            }
        }
        switch (total) {
            case 1:
                total++;
                break;
            default:
                total--;
        }
        System.out.println(greeter.hello() + size + builder + read("x") + twice(3) + counter);
    }
}
