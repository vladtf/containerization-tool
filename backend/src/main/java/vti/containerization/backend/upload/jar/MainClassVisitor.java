package vti.containerization.backend.upload.jar;

import aj.org.objectweb.asm.ClassVisitor;
import aj.org.objectweb.asm.MethodVisitor;
import aj.org.objectweb.asm.Opcodes;

public class MainClassVisitor extends ClassVisitor {
    private String className;
    private boolean hasMainMethod;

    public MainClassVisitor() {
        super(Opcodes.ASM9);
        hasMainMethod = false;
    }

    @Override
    public void visit(int version, int access, String name, String signature, String superName, String[] interfaces) {
        this.className = name.replace('/', '.');
    }

    @Override
    public MethodVisitor visitMethod(int access, String name, String descriptor, String signature, String[] exceptions) {
        if ("main".equals(name) && "([Ljava/lang/String;)V".equals(descriptor)) {
            hasMainMethod = true;
        }
        return null;
    }

    public boolean hasMainMethod() {
        return hasMainMethod;
    }

    public String getClassName() {
        return className;
    }
}
