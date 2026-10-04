// Java demo: common mistakes that SyntaxLens finds.
public class ErrorsDemo {
    public static void main(String[] args) {
        int count = 10
        double price = 5 + * 2;
        String name = "Ada;
        char grade = 'AB';
        int 2nd = 3;
        if (count > 5 {
            System.out.println("big");
        }
        for (int i = 0, i < 3, i++) {
            System.out.println(i);
        }
        if count > 0 {
            count--;
        }
        int octal = 09;
        while (count > 0);
        break;
    }
}
