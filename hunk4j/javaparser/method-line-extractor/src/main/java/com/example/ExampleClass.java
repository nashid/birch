// File: ExampleClass.java
public class ExampleClass {

    public void sayHello() {
        System.out.println("Hello, world!");
    }

    private int add(int a, int b) {
        return a + b;
    }

    protected void printMessage(String message) {
        if (message == null || message.isEmpty()) {
            System.out.println("No message provided.");
        } else {
            System.out.println("Message: " + message);
        }
    }

    public static void main(String[] args) {
        ExampleClass example = new ExampleClass();
        example.sayHello();
        System.out.println("Sum: " + example.add(3, 4));
        example.printMessage("JavaParser rocks!");




        
    }
}
