static int
arch_set_error(struct tcb *tcp)
{
	nios2_regs.regs[7] = 1;
	nios2_regs.regs[2] = -tcp->u_error;
	return set_regs(tcp->pid);
}
