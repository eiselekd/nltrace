static int
arch_set_error(struct tcb *tcp)
{
	arm_regs.ARM_r0 = -tcp->u_error;
	return set_regs(tcp->pid);
}
