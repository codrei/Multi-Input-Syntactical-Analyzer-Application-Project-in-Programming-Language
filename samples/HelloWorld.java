// A small, valid Java program used to demonstrate the Java rules.
public class HelloWorld {
    public static void main(String[] args) {
        int count = 3;
        char grade = 'A';
        double average = 91.5;
        String name = "SyntaxLens";

        for (int i = 0; i < count; i++) {
            System.out.println("Hello from " + name + " #" + (i + 1));
        }

        /* Block comments and // markers inside strings are handled too. */
        if (average >= 90.0 && grade == 'A') {
            System.out.println("Excellent! // not a comment");
        }
    }
}
